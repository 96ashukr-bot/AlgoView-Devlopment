import React from 'react';
import { Col, Row } from 'reactstrap';
import { CurrenciesWidgets } from '../../../Data/Crypto';
import BuyCard from './BuyCard';
import CurrencyWidget from '../../Common/CommonWidgets/CurrencyWidget';
import MarketGraph from './MarketGraph';
import MyCurrencies from './MyCurrencies';
import SellCard from './SellCard';

const MainGrid = () => {
  return (
    <Col xxl='6' xl='8' className='box-col-8e'>
      <Row>
        {CurrenciesWidgets.map((item, i) => (
          <Col key={i} sm='4'>
            <CurrencyWidget data={item} />
          </Col>
        ))}
        <Col xl='12'>
          <MarketGraph />
        </Col>
        <Col xl='12'>
          <MyCurrencies />
        </Col>
        <Col sm='6'>
          <BuyCard />
        </Col>
        <Col sm='6'>
          <SellCard />
        </Col>
      </Row>
    </Col>
  );
};

export default MainGrid;
