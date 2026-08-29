import HazardStripe from "../layout/HazardStripe";

function Hero() {
  return (
    <section className="hero-section">
      <div className="hero-label">
        <span className="hero-label-line" />

        VGG19 + YOLOv8 · DUAL-MODEL ROAD SCANNING
      </div>

      <h1>
        Spot the pothole
        <br />

        <span>before it spots your tire.</span>
      </h1>

      <p>
        Upload a road image and RoadGuard-AI analyzes it using
        complementary AI models to identify road surface damage
        and pinpoint where it occurs.
      </p>

      <HazardStripe />
    </section>
  );
}

export default Hero;