import { useEffect, useState } from "react";
import LoadingScreen from "../../screens/loading-screen/loading-screen";
import { fetchUrl } from "../../utils/fetch";
import { SearchGroup, SearchGroupTitle, SearchResultItem } from "./search-modal";
import { CONFIG, INFRAHUB_API_SERVER_URL } from "../../config/config";
import { Icon } from "@iconify-icon/react";
import { useDebounce } from "../../hooks/useDebounce";

type SearchProps = {
  query: string;
};
export const SearchDocs = ({ query }: SearchProps) => {
  const queryDebounced = useDebounce(query, 300);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let ignore = false;
    setLoading(true);
    const cleanedValue = queryDebounced.trim();

    fetchUrl(CONFIG.SEARCH_URL(cleanedValue)).then((data) => {
      if (ignore) return;
      setLoading(false);
      setResults(data);
    });

    return () => {
      ignore = true;
    };
  }, [queryDebounced]);

  if (loading) {
    return (
      <div className="h-52 flex items-center justify-center">
        <LoadingScreen hideText />
      </div>
    );
  }

  if (results.length === 0)
    return (
      <SearchGroup>
        <SearchResultItem to={`${INFRAHUB_API_SERVER_URL}/docs/search?q=${query}`} target="_blank">
          <Icon icon="mdi:book-open-blank-variant-outline" className="text-lg" />
          Search in docs: <span className="font-semibold">{query}</span>
        </SearchResultItem>
      </SearchGroup>
    );

  const firstThreeMatches = results.slice(0, 3);
  return (
    <SearchGroup>
      <SearchGroupTitle>Documentation</SearchGroupTitle>

      {firstThreeMatches.map((doc: SearchDocsResultProps) => (
        <DocsResults key={doc.url} breadcrumb={doc.breadcrumb} title={doc.title} url={doc.url} />
      ))}
    </SearchGroup>
  );
};

type SearchDocsResultProps = {
  breadcrumb: string[];
  title: string;
  url: string;
};

const DocsResults = ({ breadcrumb, title, url }: SearchDocsResultProps) => {
  return (
    <SearchResultItem to={INFRAHUB_API_SERVER_URL + url} target="_blank">
      {breadcrumb.slice(1).map((b) => (
        <>
          <span>{b}</span>
          <Icon icon="mdi:chevron-right" />
        </>
      ))}{" "}
      <strong className="font-semibold">{title}</strong>
    </SearchResultItem>
  );
};
