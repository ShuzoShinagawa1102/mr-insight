import { useState } from "react";

export default function Logo(props: { height?: number }) {
  const height = props.height ?? 32;
  const width = Math.round(height * 5.2);
  const [imgError, setImgError] = useState(false);

  if (!imgError) {
    return (
      <img
        src="/logo.png"
        alt="みえるマン"
        height={height}
        onError={() => setImgError(true)}
        style={{ display: "block" }}
      />
    );
  }
  return (
    <svg
      width={width}
      height={height}
      viewBox="0 0 520 100"
      role="img"
      aria-label="みえるマン"
    >
      <rect width="520" height="100" fill="transparent" />
      <text
        x="0"
        y="74"
        fontFamily="system-ui, -apple-system, 'Segoe UI', 'Noto Sans JP', sans-serif"
        fontWeight="900"
        fontSize="72"
        fill="#111"
        letterSpacing="-2"
      >
        みえるマン
      </text>
      <g transform="translate(360, 18)">
        <rect x="0" y="0" rx="30" ry="30" width="140" height="64" fill="#f28c00" />
        <text
          x="70"
          y="46"
          textAnchor="middle"
          fontFamily="system-ui, -apple-system, 'Segoe UI', 'Noto Sans JP', sans-serif"
          fontWeight="800"
          fontSize="34"
          fill="#111"
        >
          企業
        </text>
      </g>
    </svg>
  );
}
