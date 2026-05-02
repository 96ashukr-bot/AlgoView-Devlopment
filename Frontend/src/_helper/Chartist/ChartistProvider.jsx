import React, { useEffect, useState } from 'react';
import Context from './index';

const ChartistProvider = (props) => {
  const [chartistData, setChartistData] = useState([]);

  useEffect(() => {
    setChartistData([]);
  }, [setChartistData]);

  return (
    <Context.Provider
      value={{
        ...props,
        chartistData,
      }}
    >
      {props.children}
    </Context.Provider>
  );
};

export default ChartistProvider;
