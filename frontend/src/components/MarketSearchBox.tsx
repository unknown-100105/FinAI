import { useEffect, useState } from "react";
import { Search } from "lucide-react";
import {
  searchMarketInstruments,
  type InstrumentSearchResult,
} from "../api/market";

type Props = {
  value: string;
  onSelect: (symbol: string) => void;
};

export function MarketSearchBox({ value, onSelect }: Props) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<InstrumentSearchResult[]>([]);

  useEffect(() => {
    const text = query.trim();
    if (text.length < 2) {
      setResults([]);
      return;
    }

    const timer = window.setTimeout(() => {
      void searchMarketInstruments(text, 8)
        .then((response) => setResults(response.results))
        .catch(() => setResults([]));
    }, 250);

    return () => window.clearTimeout(timer);
  }, [query]);

  return (
    <div className="market-search-box">
      <div className="instrument-search">
        <Search size={15} />
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder={value || "Search any stock, ETF, fund, index, FX or crypto…"}
          aria-label="Search financial instruments"
        />
      </div>

      {results.length > 0 && (
        <div className="instrument-results">
          {results.map((result) => (
            <button
              type="button"
              key={(result.symbol || "") + (result.exchange || "")}
              onClick={() => {
                onSelect(result.symbol);
                setQuery("");
                setResults([]);
              }}
            >
              <span>
                <strong>{result.symbol}</strong>
                <small>{result.name}</small>
              </span>
              <em>
                {result.asset_type}
                {result.exchange ? " · " + result.exchange : ""}
              </em>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default MarketSearchBox;
