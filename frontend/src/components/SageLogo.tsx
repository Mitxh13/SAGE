import React from 'react';

interface SageLogoProps {
  size?: number | string;
  className?: string;
  variant?: 'mark' | 'full' | 'framed';
}

export const SageLogo: React.FC<SageLogoProps> = ({
  size = 24,
  className = '',
  variant = 'mark',
}) => {
  const pixelSize = typeof size === 'number' ? `${size}px` : size;

  if (variant === 'framed') {
    return (
      <svg
        width={pixelSize}
        height={pixelSize}
        viewBox="0 0 120 120"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className={`inline-block shrink-0 ${className}`}
      >
        <defs>
          <linearGradient id="sageLeafGradFramed" x1="20%" y1="0%" x2="80%" y2="100%">
            <stop offset="0%" stopColor="#4E7A60" />
            <stop offset="50%" stopColor="#2D4D3B" />
            <stop offset="100%" stopColor="#1B3024" />
          </linearGradient>
          <linearGradient id="sageAccentGradFramed" x1="0%" y1="100%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#8EB39D" />
            <stop offset="60%" stopColor="#A7C7B3" />
            <stop offset="100%" stopColor="#D6E6DC" />
          </linearGradient>
          <linearGradient id="flameGradFramed" x1="50%" y1="100%" x2="50%" y2="0%">
            <stop offset="0%" stopColor="#3A604B" />
            <stop offset="50%" stopColor="#6AA180" />
            <stop offset="100%" stopColor="#B2DAC0" />
          </linearGradient>
        </defs>

        <rect
          x="6"
          y="6"
          width="108"
          height="108"
          rx="28"
          fill="#E2ECE5"
          stroke="#8EB39D"
          strokeWidth="2.5"
        />

        <g transform="translate(10, 10)">
          <path
            d="M50 14 C32 14, 18 30, 20 54 C21 68, 29 80, 42 84 C48 86, 52 86, 58 84 C71 80, 79 68, 80 54 C82 30, 68 14, 50 14 Z"
            fill="url(#sageLeafGradFramed)"
          />
          <path
            d="M50 18 C36 28, 28 44, 30 60 C31 70, 38 78, 48 81 C44 75, 42 66, 43 56 C44 44, 49 32, 50 18 Z"
            fill="url(#sageAccentGradFramed)"
            opacity="0.9"
          />
          <path
            d="M50 24 C53 34, 58 40, 61 48 C64 56, 62 66, 56 72 C53 75, 49 77, 46 78 C52 76, 57 71, 58 64 C59 56, 55 50, 52 42 C50 36, 49 30, 50 24 Z"
            fill="url(#flameGradFramed)"
          />
          <circle cx="50" cy="19" r="3.5" fill="#FFFFFF" stroke="#2D4D3B" strokeWidth="1.2" />
          <circle cx="50" cy="46" r="2" fill="#D6E6DC" />
        </g>
      </svg>
    );
  }

  // Pure Vector Mark (scalable, adapts to currentColor or brand gradients)
  return (
    <svg
      width={pixelSize}
      height={pixelSize}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={`inline-block shrink-0 ${className}`}
    >
      <defs>
        <linearGradient id="sageMarkGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#4E7A60" />
          <stop offset="60%" stopColor="#2D4D3B" />
          <stop offset="100%" stopColor="#1B3024" />
        </linearGradient>
        <linearGradient id="sageInnerGrad" x1="0%" y1="100%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#8EB39D" />
          <stop offset="100%" stopColor="#C4DDD0" />
        </linearGradient>
      </defs>

      {/* Outer S-Curved Botanical Leaf & Socratic Torch Silhouette */}
      <path
        d="M50 8 C28 8, 12 28, 14 56 C15 72, 25 86, 40 90 C47 92, 53 92, 60 90 C75 86, 85 72, 86 56 C88 28, 72 8, 50 8 Z"
        fill="url(#sageMarkGrad)"
      />

      {/* S-Stem Fold (The 'S' shape) */}
      <path
        d="M50 14 C34 26, 24 45, 26 63 C28 75, 36 84, 48 87 C43 80, 40 70, 41 58 C42 44, 48 30, 50 14 Z"
        fill="url(#sageInnerGrad)"
        opacity="0.85"
      />

      {/* Central Wisdom Flame Tongue */}
      <path
        d="M50 20 C54 32, 60 40, 63 50 C66 60, 63 71, 57 78 C53 82, 48 84, 44 85 C51 83, 58 77, 59 69 C60 60, 56 52, 52 43 C50 36, 49 28, 50 20 Z"
        fill="#8EB39D"
      />

      {/* Socratic Spark of Insight */}
      <circle cx="50" cy="15" r="4" fill="#FFFFFF" />
      <circle cx="50" cy="48" r="2.5" fill="#D6E6DC" />
    </svg>
  );
};
