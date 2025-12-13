import React from 'react';
import { Search, Loader2 } from 'lucide-react';

export default function SearchInput({ 
  value, 
  onChange, 
  onSubmit, 
  placeholder = "Search...", 
  loading = false,
  className = ""
}) {
  const handleSubmit = (e) => {
    e.preventDefault();
    if (value.trim() && onSubmit) {
      onSubmit(value);
    }
  };

  return (
    <form onSubmit={handleSubmit} className={`relative ${className}`}>
      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          data-testid="search-input"
          className="
            w-full bg-surface border-2 border-border rounded-sm
            pl-12 pr-4 py-4 text-white text-lg
            placeholder:text-text-muted
            focus:border-primary focus:ring-0
            transition-colors duration-200
          "
        />
        {loading && (
          <Loader2 className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-primary animate-spin" />
        )}
      </div>
      <button
        type="submit"
        data-testid="search-submit"
        disabled={loading || !value.trim()}
        className="
          absolute right-2 top-1/2 -translate-y-1/2
          bg-primary text-black font-bold uppercase tracking-wide text-xs
          px-4 py-2 rounded-sm
          hover:bg-primary-hover disabled:opacity-50 disabled:cursor-not-allowed
          transition-colors duration-200
        "
      >
        {loading ? 'Searching...' : 'Search'}
      </button>
    </form>
  );
}
