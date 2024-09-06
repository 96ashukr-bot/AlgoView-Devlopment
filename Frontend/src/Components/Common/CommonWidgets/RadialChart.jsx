import React from 'react';
import ReactApexChart from 'react-apexcharts';
import { RadialProgressChart } from '../../../Data/Social/Chart';

const RadialChart = ({ chartData }) => {
  const updatedOption = {
    ...RadialProgressChart,
    series: chartData.series,
    options: {
      ...RadialProgressChart.options,
      chart: {
        dropShadow: {
          ...RadialProgressChart.options.chart.dropShadow,
          color: [...chartData.color],
        },
      },
      colors: chartData.color,
    },
  };
  return <ReactApexChart type='radialBar' height={130} options={updatedOption.options} series={updatedOption.series} />;
};

export default RadialChart;
