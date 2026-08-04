import { Link } from "react-router-dom";
import { StarRating } from "./StarRating";

interface ShowCardProps {
  tvmazeShowId: number;
  name: string;
  image: string | null;
  rating: number | null;
}

export function ShowCard({ tvmazeShowId, name, image, rating }: ShowCardProps) {
  return (
    <Link to={`/shows/${tvmazeShowId}`} className="show-card">
      <div className="show-card-image">
        {image ? <img src={image} alt={name} /> : <div className="show-card-image-placeholder" />}
      </div>
      <p className="show-card-name">{name}</p>
      <StarRating value={rating} readOnly size="small" />
    </Link>
  );
}
