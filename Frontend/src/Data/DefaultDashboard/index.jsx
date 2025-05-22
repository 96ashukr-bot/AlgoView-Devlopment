import { Widgets2ChartData, Widgets2ChartData2, } from './Chart';

export const WidgetsData = {
  title: 'Purchase',
  gros: 50,
  total: 10_000,
  color: 'secondary',
  icon: 'cart',
};

export const WidgetsData2 = {
  title: 'Sales return',
  gros: 20,
  total: 7000,
  color: 'warning',
  icon: 'return-box',
};
export const WidgetsData3 = {
  title: 'Sales',
  gros: 70,
  total: 4_200,
  color: 'primary',
  icon: 'tag',
};
export const WidgetsData4 = {
  title: 'Purchase rate',
  gros: 70,
  total: 5700,
  color: 'success',
  icon: 'rate',
};

export const Widgets2Data = {
  title: 'Orders',
  total: '1,80k',
  chart: Widgets2ChartData,
};
export const Widgets2Data2 = {
  title: 'Profit',
  total: '6,90k',
  chart: Widgets2ChartData2,
};

export const getWidgetsData = (subAdminsData, inactiveClientData, activeClientData) => {
  return [
    {
      title: 'Sub Admins',
      gros: 0, 
      total: subAdminsData?.count || 0, 
      color: 'warning',
      icon: "rate",
    },
    {
      title: 'Inactive Clients',
      gros: 0, 
      total: inactiveClientData?.count || 0, 
      color: 'secondary',
      icon: 'rate',
    },
    {
      title: 'Active Clients',
      gros: 0, 
      total: activeClientData?.count || 0, 
      color: 'primary',
      icon: 'rate',
    },
  ];
};

