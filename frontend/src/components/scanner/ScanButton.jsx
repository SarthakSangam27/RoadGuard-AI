import {
  ScanLine,
} from "lucide-react";

function ScanButton({
  onClick,
  disabled,
  scanning,
}) {
  return (
    <button
      type="button"
      className="scan-button"
      onClick={onClick}
      disabled={disabled}
    >
      <ScanLine size={18} />

      <span>
        {scanning
          ? "Analyzing..."
          : "Run Detection"}
      </span>
    </button>
  );
}

export default ScanButton;