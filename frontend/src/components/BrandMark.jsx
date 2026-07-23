export default function BrandMark({ className = 'h-9 w-9' }) {
  return (
    <svg aria-hidden="true" className={className} viewBox="0 0 40 40">
      <path d="M20 3 35 11v18l-15 8L5 29V11z" fill="#d7f0df" />
      <path d="M12 13h16M12 20h16M12 27h10" stroke="#103c37" strokeWidth="2.5" />
      <circle cx="29" cy="27" r="4" fill="#d89434" />
    </svg>
  )
}
