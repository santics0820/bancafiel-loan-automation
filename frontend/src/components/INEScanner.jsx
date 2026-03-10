import React, { useRef, useState, useCallback, useEffect, useMemo } from 'react';
import Webcam from 'react-webcam';
import './INEScanner.css';

const STEPS = [
  { key: 'card-front', label: 'INE Frontal' },
  { key: 'card-back',  label: 'INE Trasera' },
  { key: 'face',       label: 'Selfie'      },
];

const INSTRUCTIONS = {
  'card-front': { main: 'Alinea el FRENTE de tu INE dentro del recuadro', hint: 'Asegúrate de que todos los datos sean legibles' },
  'card-back':  { main: 'Voltea tu INE y alinea la PARTE TRASERA',        hint: 'Incluye los bordes completos de la credencial'  },
  'face':       { main: 'Centra tu rostro dentro del óvalo',              hint: 'Mantén expresión neutral y buena iluminación'  },
};

// Must match CSS percentages
const GUIDE = {
  card: { widthPct: 0.72, ratio: 1.585 },
  face: { widthPct: 0.62, ratio: 0.73  },
};

// Fallback chain for back-camera constraint across all browsers:
// level 0 → { exact: 'environment' }  — forces back cam (Chrome Android, modern Safari/Firefox)
// level 1 → { ideal: 'environment' }  — prefers back cam, won't throw if unavailable
// level 2 → no facingMode             — last resort: browser picks any camera
const BACK_CAMERA_LEVELS = [
  { facingMode: { exact: 'environment' } },
  { facingMode: { ideal: 'environment' } },
  {},
];

const INEScanner = ({ onCapture, onBack }) => {
  const webcamRef                       = useRef(null);
  const [capturedImg, setCapturedImg]   = useState(null);
  const [mode, setMode]                 = useState('card-front');
  const [frontImg, setFrontImg]         = useState(null);
  const [backCamLevel, setBackCamLevel] = useState(0);
  const [cameraError, setCameraError]   = useState(null);

  const isCardMode = mode !== 'face';
  const stepIndex  = STEPS.findIndex(s => s.key === mode);

  // Reset fallback level whenever we switch between card ↔ face
  useEffect(() => {
    setBackCamLevel(0);
    setCameraError(null);
  }, [isCardMode]);

  const videoConstraints = useMemo(() => {
    if (!isCardMode) {
      // Selfie: front cam, portrait preferred
      return {
        facingMode: { ideal: 'user' },
        width:  { ideal: 720  },
        height: { ideal: 1280 },
      };
    }
    // Card: back cam with fallback chain
    return {
      width:  { ideal: 1920 },
      height: { ideal: 1080 },
      ...BACK_CAMERA_LEVELS[backCamLevel],
    };
  }, [isCardMode, backCamLevel]);

  const handleCameraError = useCallback((err) => {
    console.warn('INEScanner camera error:', err?.name, err?.message);
    if (backCamLevel < BACK_CAMERA_LEVELS.length - 1) {
      // Try next fallback
      setBackCamLevel(prev => prev + 1);
    } else {
      setCameraError('No se pudo acceder a la cámara. Verifica los permisos del navegador.');
    }
  }, [backCamLevel]);

  // Capture and crop to the exact guide area
  const capture = useCallback(() => {
    const screenshot = webcamRef.current?.getScreenshot();
    if (!screenshot) return;
    const guide = isCardMode ? GUIDE.card : GUIDE.face;

    const img = new Image();
    img.onload = () => {
      const imgW = img.naturalWidth;
      const imgH = img.naturalHeight;

      let cropW = imgW * guide.widthPct;
      let cropH = cropW / guide.ratio;
      if (cropH > imgH) { cropH = imgH; cropW = cropH * guide.ratio; }
      if (cropW > imgW) { cropW = imgW; cropH = cropW / guide.ratio; }

      const sx = Math.max(0, (imgW - cropW) / 2);
      const sy = Math.max(0, (imgH - cropH) / 2);

      const canvas     = document.createElement('canvas');
      canvas.width     = Math.round(cropW);
      canvas.height    = Math.round(cropH);
      canvas.getContext('2d').drawImage(img, sx, sy, cropW, cropH, 0, 0, cropW, cropH);

      setCapturedImg(canvas.toDataURL('image/jpeg', 0.95));
    };
    img.src = screenshot;
  }, [isCardMode]);

  const combineFrontBack = (frontDataUrl, backDataUrl) => {
    return new Promise((resolve) => {
      const front = new Image();
      const back  = new Image();
      front.onload = () => {
        back.onload = () => {
          const canvas  = document.createElement('canvas');
          const gap     = 20;
          canvas.width  = Math.max(front.width, back.width);
          canvas.height = front.height + gap + back.height;
          const ctx = canvas.getContext('2d');
          ctx.fillStyle = '#ffffff';
          ctx.fillRect(0, 0, canvas.width, canvas.height);
          ctx.drawImage(front, 0, 0);
          ctx.drawImage(back,  0, front.height + gap);
          canvas.toBlob((blob) => resolve(blob), 'image/jpeg', 0.95);
        };
        back.src = backDataUrl;
      };
      front.src = frontDataUrl;
    });
  };

  const confirm = () => {
    if (mode === 'card-front') {
      setFrontImg(capturedImg);
      setCapturedImg(null);
      setMode('card-back');
    } else if (mode === 'card-back') {
      combineFrontBack(frontImg, capturedImg).then((blob) => {
        if (onCapture) onCapture(blob, 'card-combined');
      });
      setCapturedImg(null);
      setMode('face');
    } else if (mode === 'face') {
      if (onCapture) onCapture(null, 'face');
      setCapturedImg(null);
    }
  };

  const retake = () => setCapturedImg(null);

  return (
    <div className="ine-scanner">

      {/* Header: ← volver | step indicators */}
      <div className="ine-steps">
        <button className="ine-back-btn" onClick={onBack}>← Volver</button>
        <div className="ine-steps-track">
          {STEPS.map((step, i) => (
            <React.Fragment key={step.key}>
              {i > 0 && <div className="ine-step-divider" />}
              <div className={`ine-step ${i === stepIndex ? 'active' : ''} ${i < stepIndex ? 'done' : ''}`}>
                <span className="ine-step-dot" />
                {step.label}
              </div>
            </React.Fragment>
          ))}
        </div>
      </div>

      {cameraError ? (
        <div className="ine-camera-error">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#f87171" strokeWidth="1.5">
            <path d="M12 9v4M12 17h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
          </svg>
          <p>{cameraError}</p>
        </div>
      ) : !capturedImg ? (
        <>
          <div className={`ine-camera${isCardMode ? '' : ' face-mode'}`}>
            <Webcam
              audio={false}
              ref={webcamRef}
              screenshotFormat="image/jpeg"
              videoConstraints={videoConstraints}
              mirrored={!isCardMode}
              onUserMediaError={handleCameraError}
              style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
            />
            <div className="ine-overlay">
              {isCardMode ? <div className="ine-guide" /> : <div className="face-guide" />}
            </div>
          </div>

          <div className="ine-actions">
            <p className="ine-instruction-text">
              {INSTRUCTIONS[mode].main}
              <span>{INSTRUCTIONS[mode].hint}</span>
            </p>
            <div className="ine-actions-buttons">
              <button className="ine-btn-primary" onClick={capture}>
                Tomar foto
              </button>
            </div>
          </div>
        </>
      ) : (
        <>
          <div className={`ine-camera${isCardMode ? '' : ' face-mode'}`}>
            <img src={capturedImg} alt="Captura" className="ine-preview" />
          </div>
          <div className="ine-actions">
            <div className="ine-actions-buttons">
              <button className="ine-btn-primary" onClick={confirm}>
                Confirmar foto
              </button>
              <button className="ine-btn-reject" onClick={retake}>
                Volver a tomar
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default INEScanner;
