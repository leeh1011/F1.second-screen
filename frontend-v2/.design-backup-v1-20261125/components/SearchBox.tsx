type SearchBoxProps = {
  value: string;
  onChange: (value: string) => void;
};

function SearchBox({ value, onChange }: SearchBoxProps) {
  return (
    <div className="search-box">
      <input
        className="search"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="드라이버 이름 검색"
        aria-label="드라이버 이름 검색"
      />
      {value && (
        <button
          type="button"
          className="clear"
          onClick={() => onChange("")}
          aria-label="검색어 지우기"
        >
          ×
        </button>
      )}
    </div>
  );
}

export default SearchBox;
