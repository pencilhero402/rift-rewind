import React from 'react';

const StarRating = ({ averagePercentile, maxStars = 5, size = 24 }) => {
  const starRating = averagePercentile * maxStars;

  const renderStars = () => {
    const stars = [];
    for (let i = 1; i <= maxStars; i++) {
      if (starRating >= i) {
        stars.push(<span key={i} style={{ color: 'yellow', fontSize: size }}>★</span>);
      } else if (starRating >= i - 0.5) {
        stars.push(<span key={i} style={{ color: 'yellow', fontSize: size }}>☆</span>); // half-star placeholder
      } else {
        stars.push(<span key={i} style={{ color: 'lightgray', fontSize: size }}>★</span>);
      }
    }
    return stars;
  };

  return (
    <div>
      {renderStars()}
    </div>
  );
};

export default StarRating;
