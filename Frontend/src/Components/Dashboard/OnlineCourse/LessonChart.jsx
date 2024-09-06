import React from 'react';
import ReactApexChart from 'react-apexcharts';
import { LessonChartOption } from '../../../Data/OnlineCourse/ChartData';

const LessonChart = ({ chartData }) => {
  const updateChartOption = {
    ...LessonChartOption,
    series: chartData.series,
    options: {
      ...LessonChartOption.options,
      colors: chartData.color,
    },
  };
  return <ReactApexChart type='donut' height={80} options={updateChartOption.options} series={updateChartOption.series} />;
};

export default LessonChart;
