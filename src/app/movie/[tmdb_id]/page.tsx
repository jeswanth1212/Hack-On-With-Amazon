import MovieDetailPage from '../../../components/movie/MovieDetailPage';

export default function MoviePage({ params }: { params: { tmdb_id: string } }) {
  return <MovieDetailPage tmdbId={params.tmdb_id} />;
} 