import { useEffect, useState } from "react";

import { fetchEvidenceBlob } from "../services/cases";

export function EvidencePanel({ title, assetUrl, className = "" }: { title: string; assetUrl?: string | null; className?: string }) {
  const [src, setSrc] = useState<string | null>(null);

  useEffect(() => {
    if (!assetUrl) return;
    let currentUrl: string | null = null;
    fetchEvidenceBlob(assetUrl)
      .then((blob) => {
        currentUrl = URL.createObjectURL(blob);
        setSrc(currentUrl);
      })
      .catch(() => setSrc(null));
    return () => {
      if (currentUrl) URL.revokeObjectURL(currentUrl);
    };
  }, [assetUrl]);

  return (
    <div className={`surface evidence-panel ${className}`}>
      <div className="panel-header">
        <h3>{title}</h3>
      </div>
      {src ? <img src={src} alt={title} className="evidence-image" /> : <div className="empty-media">لا تتوفر معاينة</div>}
    </div>
  );
}
