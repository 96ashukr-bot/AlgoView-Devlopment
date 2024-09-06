import React, { Fragment } from 'react';
import { Container, Row } from 'reactstrap';
import { Breadcrumbs } from '../../../AbstractElements';
import BarChartsWidgets from './BarChartsWidgets';
import ChartWidgets from './ChartWidgets';
import CryptoAnnotations from './CryptoAnnotations';
import CryptocurrencyPrices from './CryptocurrencyPrices';
import FinanceChart from './FinanceChart';
import LiveChart from './LiveChart';
import MonthlySaleChart from './MonthlySaleChart';
import OrderStatusProgressChart from './OrderStatus';
import OrderStatusChart from './OrderStatusChart';
import SkillStatusChart from './SkillStatus';
import TurnoverChart from './TurnoverChart';
import UsesChart from './UsesChart';
import StockMarket from './StockMarket';

const ChartComponent = () => {
  return (
    <Fragment>
      <Breadcrumbs mainTitle='Chart' parent='Widgets' title='Chart' />
      <Container fluid={true} className='chart-widget'>
        {/* <!-- Chart widget top Start--> */}
        <ChartWidgets />
        {/* <!-- Chart widget top Ends-->
                <!-- Chart widget with bar chart Start--> */}
        <BarChartsWidgets />
        {/* <!-- small widgets Start--> */}
        <Row>
          <SkillStatusChart />
          <OrderStatusProgressChart />
          <LiveChart />
          <TurnoverChart />
          <CryptocurrencyPrices />
          <CryptoAnnotations />
          <StockMarket />
          <FinanceChart />
          <OrderStatusChart />
          <MonthlySaleChart />
          <UsesChart />
        </Row>
      </Container>
    </Fragment>
  );
};

export default ChartComponent;
