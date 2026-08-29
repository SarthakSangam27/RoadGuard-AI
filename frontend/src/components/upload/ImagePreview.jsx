import { useEffect, useState } from "react";

import DetectionOverlay from "../results/DetectionOverlay";

function ImagePreview({
  file,
  scanning,
  detections = [],
}) {
  const [imageUrl, setImageUrl] =
    useState("");

  useEffect(() => {
    if (!file) {
      setImageUrl("");
      return;
    }

    const url =
      URL.createObjectURL(file);

    setImageUrl(url);

    return () => {
      URL.revokeObjectURL(url);
    };
  }, [file]);

  if (!file || !imageUrl) {
    return null;
  }

  return (
    <div className="image-preview">
      <img
        src={imageUrl}
        alt="Uploaded road"
      />

      {detections.length > 0 && (
        <DetectionOverlay
          detections={detections}
        />
      )}

      {scanning && (
        <>
          <div className="scan-line" />

          <div className="scan-status">
            <span />

            ANALYZING SURFACE —
            VGG19 + YOLOv8
          </div>
        </>
      )}
    </div>
  );
}

export default ImagePreview;