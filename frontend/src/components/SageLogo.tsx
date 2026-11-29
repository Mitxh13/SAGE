import React from 'react';

interface SageLogoProps {
  size?: number | string;
  className?: string;
}

export const SageLogo: React.FC<SageLogoProps> = ({
  size = 24,
  className = '',
}) => {
  const pixelSize = typeof size === 'number' ? `${size}px` : size;

  return (
    <svg
      width={pixelSize}
      height={pixelSize}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={`inline-block shrink-0 select-none ${className}`}
    >
      <defs>
        <linearGradient id="sageLeftGradComponent" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#3A634B" />
          <stop offset="60%" stopColor="#244433" />
          <stop offset="100%" stopColor="#182E22" />
        </linearGradient>
        <linearGradient id="sageRightGradComponent" x1="0%" y1="100%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#3A634B" />
          <stop offset="40%" stopColor="#558B6E" />
          <stop offset="100%" stopColor="#7BB594" />
        </linearGradient>
        <linearGradient id="sageCoreGradComponent" x1="50%" y1="100%" x2="50%" y2="0%">
          <stop offset="0%" stopColor="#527E64" />
          <stop offset="50%" stopColor="#8EB39D" />
          <stop offset="100%" stopColor="#B8DCBF" />
        </linearGradient>
      </defs>

      {/* Primary Left Sage Leaf & S-Curve Ribbon */}
      <path
        d="M 50 8 C 30 18, 16 38, 16 58 C 16 76, 32 90, 50 92 C 43 82, 28 70, 28 54 C 28 36, 40 20, 50 8 Z"
        fill="url(#sageLeftGradComponent)"
      />

      {/* Interlocking Right Socratic Leaf Ribbon */}
      <path
        d="M 50 92 C 70 82, 84 62, 84 42 C 84 24, 68 10, 50 8 C 57 18, 72 30, 72 46 C 72 64, 60 80, 50 92 Z"
        fill="url(#sageRightGradComponent)"
      />

      {/* Central Socratic Flame of Insight */}
      <path
        d="M 50 25 C 44 38, 42 52, 44 66 C 46 76, 51 82, 50 86 C 53 82, 57 74, 56 64 C 55 50, 53 38, 50 25 Z"
        fill="url(#sageCoreGradComponent)"
      />

      {/* Guiding Beacon Node at Apex */}
      <circle cx="50" cy="16" r="3.5" fill="#1B3024" />
      <circle cx="50" cy="16" r="1.8" fill="#E2ECE5" />
    </svg>
  );
};
