import MovieDetailPage from '../../../components/movie/MovieDetailPage';

export default async function MoviePage({ params }: { params: { tmdb_id: string } }) {
  return <MovieDetailPage tmdbId={params.tmdb_id} />;
} 