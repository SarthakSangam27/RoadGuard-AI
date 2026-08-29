function SampleImages({ onSelect }) {
  return (
    <div className="sample-row">
      <span>
        No image handy? Try a sample:
      </span>

      <button
        onClick={() => onSelect("pothole")}
      >
        Sample: Pothole road
      </button>

      <button
        onClick={() => onSelect("clear")}
      >
        Sample: Clear road
      </button>
    </div>
  );
}

export default SampleImages;