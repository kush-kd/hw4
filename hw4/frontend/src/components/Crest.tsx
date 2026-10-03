// A real brand mark instead of a plain "CC" square — a shield crest, the
// classic collegiate-heritage device (see design.md for why this replaced
// the placeholder badge).
export default function Crest({ size = 34, className = '' }: { size?: number; className?: string }) {
  const height = Math.round(size * (76 / 64))
  return (
    <svg
      width={size}
      height={height}
      viewBox="0 0 64 76"
      className={`crest ${className}`}
      aria-hidden="true"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M32 2 L60 10 V38 C60 58 48 70 32 74 C16 70 4 58 4 38 V10 Z"
        fill="#00356b"
        stroke="#c9a44c"
        strokeWidth="2.5"
      />
      <path
        d="M32 8 L54 14.5 V37 C54 53 44 63 32 67 C20 63 10 53 10 37 V14.5 Z"
        fill="none"
        stroke="#c9a44c"
        strokeWidth="1"
        opacity="0.55"
      />
      <text
        x="32"
        y="47"
        textAnchor="middle"
        fontFamily="Fraunces, Georgia, serif"
        fontWeight="700"
        fontSize="30"
        fill="#c9a44c"
      >
        Y
      </text>
    </svg>
  )
}
