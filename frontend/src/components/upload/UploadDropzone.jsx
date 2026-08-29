import { useRef, useState } from "react";
import { Camera, Upload } from "lucide-react";

function UploadDropzone({ onFile }) {
  const inputRef = useRef(null);

  const [dragOver, setDragOver] = useState(false);

  function validateAndSelect(file) {
    if (!file) return;

    const allowedTypes = [
      "image/jpeg",
      "image/png",
      "image/webp",
      "image/bmp",
    ];

    if (!allowedTypes.includes(file.type)) {
      alert(
        "Invalid file type. Please upload JPG, PNG, WEBP, or BMP."
      );

      return;
    }

    const maxSize = 25 * 1024 * 1024;

    if (file.size > maxSize) {
      alert(
        "File is too large. Maximum size is 25MB."
      );

      return;
    }

    onFile(file);
  }

  function handleDrop(event) {
    event.preventDefault();

    setDragOver(false);

    const file =
      event.dataTransfer.files?.[0];

    validateAndSelect(file);
  }

  function handleBrowse(event) {
    const file =
      event.target.files?.[0];

    validateAndSelect(file);

    event.target.value = "";
  }

  return (
    <div
      className={`upload-dropzone ${
        dragOver ? "drag-active" : ""
      }`}
      onClick={() =>
        inputRef.current?.click()
      }
      onDragEnter={(event) => {
        event.preventDefault();
        setDragOver(true);
      }}
      onDragOver={(event) => {
        event.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={(event) => {
        event.preventDefault();
        setDragOver(false);
      }}
      onDrop={handleDrop}
    >
      <div className="upload-icon">
        {dragOver ? (
          <Upload size={42} />
        ) : (
          <Camera size={42} />
        )}
      </div>

      <h3>
        {dragOver
          ? "Release to upload"
          : "Drop a road image here,"}

        {!dragOver && (
          <>
            <br />
            or click to browse
          </>
        )}
      </h3>

      <p>
        JPG, PNG, WEBP, BMP up to 25MB
      </p>

      <input
        ref={inputRef}
        type="file"
        accept=".jpg,.jpeg,.png,.webp,.bmp"
        hidden
        onChange={handleBrowse}
      />
    </div>
  );
}

export default UploadDropzone;