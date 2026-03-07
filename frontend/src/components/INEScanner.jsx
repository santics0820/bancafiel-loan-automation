import React, { useRef, useState, useCallback } from 'react';
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

// Proporciones que deben coincidir con las del CSS
const GUIDE = {
  card: { widthPct: 0.72, ratio: 1.585 },
  face: { widthPct: 0.42, ratio: 0.73  },
};

const INEScanner = ({ onCapture, onBack }) => {
  const webcamRef                     = useRef(null);
  const [capturedImg, setCapturedImg] = useState(null);
  const [mode, setMode]               = useState('card-front');
  const [frontImg, setFrontImg]       = useState(null);

  const isCardMode = mode !== 'face';
  const stepIndex  = STEPS.findIndex(s => s.key === mode);

  const videoConstraints = {
    width: 1280,
    height: 720,
    facingMode: isCardMode ? 'environment' : 'user',
  };

  // Captura y recorta al área exacta del recuadro guía
  const capture = useCallback(() => {
    const screenshot = webcamRef.current.getScreenshot();
    const guide      = isCardMode ? GUIDE.card : GUIDE.face;

    const img  = new Image();
    img.onload = () => {
      const imgW = img.naturalWidth;
      const imgH = img.naturalHeight;

      // Clamp al tamaño real del frame para evitar sx/sy negativos
      let cropW = imgW * guide.widthPct;
      let cropH = cropW / guide.ratio;
      if (cropH > imgH) { cropH = imgH; cropW = cropH * guide.ratio; }
      if (cropW > imgW) { cropW = imgW; cropH = cropW / guide.ratio; }

      const sx = Math.max(0, (imgW - cropW) / 2);
      const sy = Math.max(0, (imgH - cropH) / 2);

      const canvas    = document.createElement('canvas');
      canvas.width    = Math.round(cropW);
      canvas.height   = Math.round(cropH);
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
          const canvas = document.createElement('canvas');
          const gap    = 20;
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
      // Combine front + back into one JPEG blob and pass to parent
      combineFrontBack(frontImg, capturedImg).then((blob) => {
        if (onCapture) onCapture(blob, 'card-combined');
      });
      setCapturedImg(null);
      setMode('face');
    } else if (mode === 'face') {
      // Selfie — just advance, no image sent to Bedrock
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

      {!capturedImg ? (
        <>
          {/* Cámara — overlay limpio, sin texto encima */}
          <div className="ine-camera">
            <Webcam
              audio={false}
              ref={webcamRef}
              screenshotFormat="image/jpeg"
              videoConstraints={videoConstraints}
              width="100%"
            />
            <div className="ine-overlay">
              {isCardMode ? <div className="ine-guide" /> : <div className="face-guide" />}
            </div>
          </div>

          {/* Instrucciones + botón fuera de la cámara */}
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
          <div className="ine-camera">
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
