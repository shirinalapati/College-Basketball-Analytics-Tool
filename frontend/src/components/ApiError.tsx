export default function ApiError({ message }: { message: string }) {
  return (
    <div className="card border-red-500/50 bg-red-950/30 text-red-200 text-sm">
      <p className="font-semibold">Could not load data</p>
      <p className="mt-1">{message}</p>
      <p className="mt-2 text-xs text-gray-400">
        Ensure the API is running:{' '}
        <code className="text-illini-orange">cd backend && uvicorn api.main:app --reload --port 8000</code>
      </p>
    </div>
  );
}
