const ReactAppFromCDN = () => {
  return (
    <div className={`alert alert-primary`}>
      This is a test of React-Bootstrap
    </div>
  );
};

ReactDOM.render(<ReactAppFromCDN />, document.querySelector("#root"));
