import { Download, FileText } from "lucide-react";

import type { AssetRow } from "../types";

type Props = {
  sessionId: string;
  assets: AssetRow[];
};

export function AssetLibrary({ assets }: Props) {
  return (
    <section className="panel">
      <div className="panel-heading split-heading">
        <div>
          <p className="eyebrow">Outputs</p>
          <h2>Asset Library</h2>
          <p>Generated program materials from the backend pipeline.</p>
        </div>
        <a className="button primary" href={assets[0]?.download_url ?? "#"} aria-disabled={!assets.length}>
          <Download size={17} />
          Download first
        </a>
      </div>
      {assets.length === 0 ? (
        <div className="empty-state">No generated assets yet.</div>
      ) : (
        <div className="asset-table" role="table" aria-label="Generated assets">
          <div className="asset-table-head" role="row">
            <span>Asset Name</span>
            <span>Type</span>
            <span>Status</span>
            <span>Actions</span>
          </div>
          {assets.map((asset) => (
            <div className="asset-row" role="row" key={asset.id}>
              <div className="asset-name">
                <span className="asset-icon">
                  <FileText size={15} />
                </span>
                <span>
                  <strong>{asset.name}</strong>
                  <small>{asset.description}</small>
                </span>
              </div>
              <span>{asset.type}</span>
              <span className="status-dot">{asset.status}</span>
              <span>
                {asset.download_url ? (
                  <a className="icon-button" href={asset.download_url} aria-label={`Download ${asset.name}`}>
                    <Download size={17} />
                  </a>
                ) : null}
              </span>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
