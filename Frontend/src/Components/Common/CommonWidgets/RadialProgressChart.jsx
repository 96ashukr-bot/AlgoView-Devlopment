import React from 'react';
import ReactApexChart from 'react-apexcharts';
import { WidgetsRadialChart } from '../../../Data/Crypto/Chart';

const RadialProgressChart = ({ chartOption, chartHeight }) => {
  const updatedOption = {
    ...WidgetsRadialChart,
    series: chartOption.chart.series,
    options: {
      ...WidgetsRadialChart.options,
      chart: {
        ...WidgetsRadialChart.options.chart,
        dropShadow: {
          ...WidgetsRadialChart.options.chart.dropShadow,
          color: chartOption.chart.color,
        },
      },
      colors: [chartOption.chart.color],
    },
  };
  return <ReactApexChart type='radialBar' height={chartHeight} series={updatedOption.series} options={updatedOption.options} />;
};

export default RadialProgressChart;
