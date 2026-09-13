// ============================================================
// RoadGuard-AI
// scanService.js
// Connects React frontend to Flask AI backend
// ============================================================


// ============================================================
// API CONFIGURATION
// ============================================================

// Vite environment variable.
//
// LOCAL:
// VITE_API_BASE_URL=http://127.0.0.1:5000
//
// PRODUCTION:
// VITE_API_BASE_URL=https://roadguard-ai-54av.onrender.com
//
// The fallback allows the frontend to work locally even if
// the .env file has not been created yet.

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:5000";


// ============================================================
// ANALYZE IMAGE
// ============================================================

export async function analyzeImage(file) {

  // ----------------------------------------------------------
  // Validate file
  // ----------------------------------------------------------

  if (!file) {
    throw new Error(
      "No image was provided."
    );
  }


  // ----------------------------------------------------------
  // Validate image type
  // ----------------------------------------------------------

  if (!file.type.startsWith("image/")) {
    throw new Error(
      "Please select a valid image file."
    );
  }


  // ----------------------------------------------------------
  // Create FormData
  // ----------------------------------------------------------

  const formData = new FormData();

  formData.append(
    "image",
    file
  );


  // ----------------------------------------------------------
  // Create request timeout
  // ----------------------------------------------------------
  //
  // ML inference can take a while, especially when VGG19 and
  // YOLOv8 need to be loaded for the first request.
  //
  // 5 minutes gives the backend enough time to complete a
  // first-time model load on a CPU-only server.

  const controller =
    new AbortController();

  const timeoutId =
    setTimeout(() => {
      controller.abort();
    }, 5 * 60 * 1000);


  try {

    // --------------------------------------------------------
    // Send image to Flask
    // --------------------------------------------------------

    const response = await fetch(
      `${API_BASE_URL}/api/scan`,
      {
        method: "POST",
        body: formData,
        signal: controller.signal,
      }
    );


    // --------------------------------------------------------
    // Read response
    // --------------------------------------------------------

    let data;

    try {

      data =
        await response.json();

    } catch (jsonError) {

      throw new Error(
        `Backend returned an invalid response. HTTP status: ${response.status}`
      );
    }


    // --------------------------------------------------------
    // Handle HTTP errors
    // --------------------------------------------------------

    if (!response.ok) {

      throw new Error(
        data?.error ||
        `Image detection failed. HTTP status: ${response.status}`
      );
    }


    // --------------------------------------------------------
    // Handle backend errors
    // --------------------------------------------------------

    if (
      data?.success === false
    ) {

      throw new Error(
        data.error ||
        "Unable to analyze image."
      );
    }


    // --------------------------------------------------------
    // Validate expected response
    // --------------------------------------------------------

    if (!data) {

      throw new Error(
        "Empty response received from backend."
      );
    }


    // --------------------------------------------------------
    // Normalize VGG19 result
    // --------------------------------------------------------

    const vgg19 = {

      label:
        data.vgg19?.label ||
        "unknown",

      confidence:
        Number(
          data.vgg19?.confidence ?? 0
        ),
    };


    // --------------------------------------------------------
    // Normalize YOLOv8 detections
    // --------------------------------------------------------

    const detections =
      Array.isArray(
        data.yolov8?.detections
      )

        ? data.yolov8.detections.map(
            (detection) => ({

              confidence:
                Number(
                  detection.confidence ?? 0
                ),

              class_id:
                Number(
                  detection.class_id ?? 0
                ),

              bboxPct: {

                x:
                  Number(
                    detection.bboxPct?.x ?? 0
                  ),

                y:
                  Number(
                    detection.bboxPct?.y ?? 0
                  ),

                w:
                  Number(
                    detection.bboxPct?.w ?? 0
                  ),

                h:
                  Number(
                    detection.bboxPct?.h ?? 0
                  ),
              },
            })
          )

        : [];


    // --------------------------------------------------------
    // Number of detections
    // --------------------------------------------------------

    const numDetections =
      Number(
        data.yolov8?.num_detections ??
        detections.length
      );


    // --------------------------------------------------------
    // Highest YOLO confidence
    // --------------------------------------------------------

    const highestConfidence =
      detections.length > 0

        ? Math.max(
            ...detections.map(
              (item) =>
                item.confidence
            )
          )

        : 0;


    // --------------------------------------------------------
    // Processing time
    // --------------------------------------------------------

    const processingTime =
      Number(
        data.processing_time_sec ?? 0
      );


    // --------------------------------------------------------
    // Final normalized result
    // --------------------------------------------------------

    return {

      success: true,

      // Final verdict
      pothole_detected:
        Boolean(
          data.pothole_detected
        ),

      // ------------------------------------------------------
      // VGG19
      // ------------------------------------------------------

      vgg19: {

        label:
          vgg19.label,

        confidence:
          vgg19.confidence,
      },

      // ------------------------------------------------------
      // YOLOv8
      // ------------------------------------------------------

      yolov8: {

        num_detections:
          numDetections,

        highest_confidence:
          highestConfidence,

        detections:
          detections,
      },

      // ------------------------------------------------------
      // Processing time
      // ------------------------------------------------------

      processing_time_sec:
        processingTime,
    };


  } catch (error) {

    // --------------------------------------------------------
    // Request timeout
    // --------------------------------------------------------

    if (
      error?.name === "AbortError"
    ) {

      throw new Error(
        "Detection timed out after 5 minutes. The AI models may be taking too long to load or run on the backend."
      );
    }


    // --------------------------------------------------------
    // Network / CORS / backend connection error
    // --------------------------------------------------------

    if (
      error instanceof TypeError
    ) {

      throw new Error(
        `Unable to connect to the Flask backend at ${API_BASE_URL}. Check that the backend is running and that CORS allows this frontend.`
      );
    }


    // --------------------------------------------------------
    // Forward meaningful error
    // --------------------------------------------------------

    throw new Error(
      error?.message ||
      "Unable to analyze image."
    );


  } finally {

    clearTimeout(
      timeoutId
    );
  }
}


// ============================================================
// HEALTH CHECK
// ============================================================

export async function checkBackendHealth() {

  try {

    const response =
      await fetch(
        `${API_BASE_URL}/api/health`
      );


    if (!response.ok) {

      return {

        status: "error",

        message:
          `Backend returned HTTP ${response.status}.`,
      };
    }


    const data =
      await response.json();


    return data;


  } catch (error) {

    return {

      status: "error",

      message:
        `Unable to connect to Flask backend at ${API_BASE_URL}.`,
    };
  }
}