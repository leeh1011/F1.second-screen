type SearchBoxProps={
    value:string;
    onChange:(value:string)=>void;
}

function SearchBox({value,onChange}:SearchBoxProps){
    return(
        <div className="search-box">
      <input
        className="search"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="드라이버 이름 검색"
      />
      {value && (
        <button className="clear" onClick={() => onChange("")}>
          ×
        </button>
      )}
        </div>
    )
}

export default SearchBox;