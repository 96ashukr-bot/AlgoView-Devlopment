import React from 'react';
import ReactApexChart from 'react-apexcharts';
import { widgetsLineChart } from '../../../Data/Crypto/Chart';

const CurrencyWidgetChart = ({ chartData }) => {
  const updatedOptions = {
    ...widgetsLineChart,
    series: [
      {
        data: chartData.series,
      },
    ],
    options: {
      ...widgetsLineChart.options,
      chart: {
        ...widgetsLineChart.options.chart,
        dropShadow: {
          ...widgetsLineChart.options.chart.dropShadow,
          color: chartData.color.flat(),
        },
      },
      colors: chartData.color,
      labels: chartData.label,
    },
  };
  return <ReactApexChart type='line' height={120} width={120} options={updatedOptions.options} series={updatedOptions.series} />;
};

export default CurrencyWidgetChart;
