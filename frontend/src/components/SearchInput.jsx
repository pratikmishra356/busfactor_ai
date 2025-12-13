import React from 'react';
import { Search, Loader2 } from 'lucide-react';

export default function SearchInput({ value, onChange, onSubmit, loading, placeholder }) {
  const handleSubmit = (e) => {
    e.preventDefault();
    if (value.trim() && !loading) {
      onSubmit(value.trim());
    }
  };

  return (
    <form onSubmit={handleSubmit} className="relative" data-testid="search-form">
      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder || 'Search...'}
          disabled={loading}
          data-testid="search-input"
          className="w-full bg-surface border border-border rounded-sm pl-12 pr-32 py-4 text-white placeholder:text-text-muted focus:outline-none focus:border-primary transition-colors font-body"
        />
        <button
          type="submit"
          disabled={loading || !value.trim()}
          data-testid="search-submit"
          className="absolute right-2 top-1/2 -translate-y-1/2 bg-primary text-black px-6 py-2 rounded-sm font-bold text-sm uppercase tracking-wide hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Loading</span>
            </>
          ) : (
            <span>Search</span>
          )}
        </button>
      </div>
    </form>
  );
}
