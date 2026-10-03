import { useEffect, useState } from "react";
import { ExternalLink, Filter, Newspaper, Search, Sparkles } from "lucide-react";
import { getMarketNews, type MarketNewsItem } from "../api/market";
import "./PlatformModules.css";

const presets = [
  ["Indian market", "Indian stock market"],
  ["Banking", "Indian banking stocks"],
  ["Technology", "Indian technology stocks"],
  ["Global", "global financial markets"],
] as const;

export function NewsHub() {
  const [query, setQuery] = useState("Indian stock market");
  const [articles, setArticles] = useState<MarketNewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = async (nextQuery = query) => {
    setLoading(true);
    setError("");
    try {
      const result = await getMarketNews(nextQuery, 16);
      setArticles(result.articles);
    } catch (requestError) {
      setArticles([]);
      setError(requestError instanceof Error ? requestError.message : "News is unavailable.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void load(); }, []);

  return (
    <section className="module-page">
      <div className="module-hero compact-hero">
        <div>
          <div className="module-kicker"><Newspaper size={14} /> News intelligence</div>
          <h1>Financial news, organized around the market.</h1>
          <p>Search companies, sectors and market themes, with publisher links kept visible.</p>
        </div>
        <div className="module-orb"><Sparkles size={23} /></div>
      </div>

      <div className="news-toolbar">
        <div className="news-search"><Search size={15} /><input value={query} onChange={(e) => setQuery(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") void load(); }} /><button type="button" onClick={() => void load()}>Search</button></div>
        <div className="news-presets">{presets.map(([label, value]) => <button type="button" key={value} className={query === value ? "active" : ""} onClick={() => { setQuery(value); void load(value); }}><Filter size={11} />{label}</button>)}</div>
      </div>

      {error && <div className="module-error">{error}</div>}
      <div className="news-grid">
        {loading ? <div className="module-empty large">Loading headlines…</div> :
          articles.length ? articles.map((article, index) => (
            <a className="news-card" key={article.title + index} href={article.link || "#"} target="_blank" rel="noreferrer">
              <div className="news-card-top"><span>{article.publisher || "Financial news"}</span><ExternalLink size={13} /></div>
              <strong>{article.title}</strong>
              <small>{article.published_at || "Latest available"}</small>
            </a>
          )) :
          <div className="module-empty large">No headlines returned for this search.</div>}
      </div>
    </section>
  );
}

export default NewsHub;
