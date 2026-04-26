import argparse
import sys
from pathlib import Path

# Add project root and backend to path so imports work correctly
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "backend"))

from PIL import Image

from worker.app.inference.model_runtime import runtime
from worker.app.inference.drawing import annotate_event, crop_box
from common.utils.plate_reading import (
    DEFAULT_CHAR_CONF_THRESHOLD,
    build_tokens,
    reconstruct_plate,
    serialize_plate_result,
)


def main():
    parser = argparse.ArgumentParser(description="Process a single image through the ITVM plate recognition pipeline.")
    parser.add_argument("--image", required=True, type=str, help="Path to input image")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--conf", type=float, default=DEFAULT_CHAR_CONF_THRESHOLD, help="Character confidence threshold")
    args = parser.parse_args()

    image_path = Path(args.image)
    if not image_path.exists():
        print(f"Error: {image_path} not found.")
        sys.exit(1)

    print(f"Loading image {image_path}...")
    image = Image.open(image_path).convert("RGB")

    print("Running violation detection model...")
    detections = runtime.detect_violations(image, max_det=50)

    from common.constants.violation_catalog import PLATE_BOX_LABEL
    plates = [d for d in detections if d["label"] == PLATE_BOX_LABEL]

    if not plates:
        print("لم يتم العثور على لوحة (No plate detected)")
        sys.exit(0)

    best_plate = sorted(plates, key=lambda x: x["confidence"], reverse=True)[0]
    print(f"Best plate detection confidence: {best_plate['confidence']:.2f}")

    plate_crop = crop_box(image, best_plate["bbox"], padding=4)

    print("Running plate recognition model...")
    plate_token_detections = runtime.detect_plate_tokens(plate_crop)

    if args.debug:
        import pprint
        print(f"\nConfidence threshold: {args.conf}")
        print(f"Raw detections ({len(plate_token_detections)} tokens):")
        tokens = build_tokens(plate_token_detections)
        for t in sorted(tokens, key=lambda x: x.confidence, reverse=True):
            status = "✓" if t.confidence >= args.conf else "✗"
            print(f"  {status} {t.normalized_label:>5} ({t.char_type:>6}) conf={t.confidence:.3f}  x_center={t.center_x:.1f}")

    plate_result = reconstruct_plate(plate_token_detections, conf_threshold=args.conf)

    print(f"\n--- Final Recognition Output ---")
    print(f"Arabic Text:    {plate_result.arabic_text_display}")
    print(f"Summary:        {plate_result.display_summary_ar}")
    print(f"Letters:        {plate_result.letters_ar}")
    print(f"Digits:         {plate_result.digits_ar}")
    print(f"Confidence:     {plate_result.plate_confidence:.2f}")
    print(f"Tokens:         {plate_result.token_count}")
    print(f"Rows:           {plate_result.row_count}")

    if args.debug:
        print(f"\nToken details:")
        for td in plate_result.token_details:
            print(f"  row={td['row_index']} {td['normalized_label']:>5} → {td['arabic_value']}  ({td['char_type']})  conf={td['confidence']:.3f}")

    overlay = [{"vehicle_bbox": best_plate["bbox"], "case_number": "TEST"}]
    annotated_bytes = annotate_event(image, detections, overlay)

    out_file = Path("annotated_output.jpg")
    out_file.write_bytes(annotated_bytes)
    print(f"\nSaved annotated result to {out_file.absolute()}")


if __name__ == "__main__":
    main()
