interface StarRatingProps {
  value: number | null;
  onRate?: (rating: number) => void;
  size?: "small" | "medium";
  readOnly?: boolean;
}

const STARS = [1, 2, 3, 4, 5];

export function StarRating({ value, onRate, size = "medium", readOnly = false }: StarRatingProps) {
  return (
    <div
      className={`star-rating star-rating-${size}${readOnly ? " star-rating-readonly" : ""}`}
      role="radiogroup"
      aria-label="Rating"
    >
      {STARS.map((star) => (
        <button
          key={star}
          type="button"
          className={`star-rating-star${value !== null && star <= value ? " filled" : ""}`}
          role="radio"
          aria-checked={value === star}
          aria-label={`${star} star${star > 1 ? "s" : ""}`}
          disabled={readOnly}
          onClick={(e) => {
            e.stopPropagation();
            onRate?.(star);
          }}
        >
          &#9733;
        </button>
      ))}
    </div>
  );
}
