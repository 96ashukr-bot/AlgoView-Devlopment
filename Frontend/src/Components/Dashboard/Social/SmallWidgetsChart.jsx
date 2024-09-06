import React from 'react';
import { SmallWidgetsChartOption } from '../../../Data/Social/Chart';

import ReactApexChart from 'react-apexcharts';

const SmallWidgetsChart = ({ chartData }) => {
  const updatedOptions = {
    ...SmallWidgetsChartOption,
    series: chartData.series,
    options: {
      ...SmallWidgetsChartOption.options,
      chart: {
        ...SmallWidgetsChartOption.options.chart,
        dropShadow: {
          ...SmallWidgetsChartOption.options.chart.dropShadow,
          color: chartData.color,
        },
      },
      annotations: {
        ...SmallWidgetsChartOption.options.annotations,
        points: [{ ...SmallWidgetsChartOption.options.annotations.points[0], marker: { ...SmallWidgetsChartOption.options.annotations.points[0].marker, fillColor: chartData.color } }],
      },

      fill: {
        ...SmallWidgetsChartOption.options.fill,
        gradient: {
          ...SmallWidgetsChartOption.options.fill.gradient,
          colorStops: SmallWidgetsChartOption.options.fill.gradient.colorStops.map((item) => {
            return { ...item, color: chartData.color };
          }),
        },
      },
      colors: [...chartData.color],
      responsive: SmallWidgetsChartOption.options.responsive.map((item) => {
        return {
          ...item,
          options: {
            ...item.options,
            annotations: {
              points: [{ ...item.options.annotations.points[0], marker: { ...item.options.annotations.points[0].marker, fillColor: chartData.color } }],
            },
          },
        };
      }),
    },
  };
  return <ReactApexChart type='line' width={95} height={89} options={updatedOptions.options} series={updatedOptions.series} />;
};

export default SmallWidgetsChart;
