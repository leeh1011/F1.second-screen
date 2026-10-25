type CardProps={
    name:string,
    team:string,
    number:number,
};

function Card({name,team,number}:CardProps){
    return(
    <div className="card">
      <h2>{name}</h2>
      <p>Team: {team}</p>
      <span className="number">{number}</span>
    </div>
  );
}

export default Card;