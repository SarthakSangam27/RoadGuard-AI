import {
  Upload,
  Brain,
  ScanSearch,
  ShieldCheck,
  ArrowDown,
} from "lucide-react";

function DocsSection() {
  return (
    <section
      className="docs-section"
      id="docs"
    >
      {/* Header */}

      <div className="docs-heading">
        <div className="docs-eyebrow">
          <span />
          HOW ROADGUARD-AI WORKS
        </div>

        <h2>
          From road image
          <br />
          <span>to road intelligence.</span>
        </h2>

        <p>
          RoadGuard-AI uses two complementary computer
          vision models. VGG19 answers whether damage is
          present, while YOLOv8 determines where the
          damage occurs.
        </p>
      </div>


      {/* Pipeline */}

      <div className="docs-pipeline">

        {/* STEP 1 */}

        <div className="pipeline-step">
          <div className="pipeline-number">
            01
          </div>

          <div className="pipeline-icon">
            <Upload size={24} />
          </div>

          <div className="pipeline-content">
            <span className="pipeline-label">
              INPUT
            </span>

            <h3>
              Upload Road Image
            </h3>

            <p>
              Provide a road image through the
              drag-and-drop interface or file browser.
            </p>
          </div>
        </div>


        <div className="pipeline-arrow">
          <ArrowDown size={20} />
        </div>


        {/* STEP 2 */}

        <div className="pipeline-step">
          <div className="pipeline-number">
            02
          </div>

          <div className="pipeline-icon classifier">
            <Brain size={24} />
          </div>

          <div className="pipeline-content">
            <span className="pipeline-label">
              CLASSIFICATION
            </span>

            <h3>
              VGG19
            </h3>

            <p>
              The classifier analyzes the complete
              road image and determines whether
              pothole damage is present.
            </p>
          </div>
        </div>


        <div className="pipeline-arrow">
          <ArrowDown size={20} />
        </div>


        {/* STEP 3 */}

        <div className="pipeline-step">
          <div className="pipeline-number">
            03
          </div>

          <div className="pipeline-icon detector">
            <ScanSearch size={24} />
          </div>

          <div className="pipeline-content">
            <span className="pipeline-label">
              OBJECT DETECTION
            </span>

            <h3>
              YOLOv8
            </h3>

            <p>
              The detector locates individual
              potholes and returns bounding boxes
              with confidence scores.
            </p>
          </div>
        </div>


        <div className="pipeline-arrow">
          <ArrowDown size={20} />
        </div>


        {/* STEP 4 */}

        <div className="pipeline-step final">
          <div className="pipeline-number">
            04
          </div>

          <div className="pipeline-icon final-icon">
            <ShieldCheck size={24} />
          </div>

          <div className="pipeline-content">
            <span className="pipeline-label">
              FINAL DECISION
            </span>

            <h3>
              Road Safety Verdict
            </h3>

            <p>
              Both model outputs are presented together
              to provide a clear, actionable road-surface
              assessment.
            </p>
          </div>
        </div>

      </div>


      {/* Model comparison */}

      <div className="docs-comparison">

        <div className="comparison-header">
          <span>
            MODEL ROLE
          </span>

          <span>
            VGG19
          </span>

          <span>
            YOLOv8
          </span>
        </div>


        <div className="comparison-row">
          <span>
            Primary purpose
          </span>

          <span>
            Classification
          </span>

          <span>
            Detection
          </span>
        </div>


        <div className="comparison-row">
          <span>
            Output
          </span>

          <span>
            Pothole / Clear
          </span>

          <span>
            Bounding boxes
          </span>
        </div>


        <div className="comparison-row">
          <span>
            Confidence
          </span>

          <span>
            Image-level
          </span>

          <span>
            Object-level
          </span>
        </div>


        <div className="comparison-row">
          <span>
            Best for
          </span>

          <span>
            Road assessment
          </span>

          <span>
            Pothole localization
          </span>
        </div>

      </div>

    </section>
  );
}

export default DocsSection;