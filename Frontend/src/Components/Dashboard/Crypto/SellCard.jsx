import React from 'react';
import { Card, CardBody, CardHeader, Form, Input, Label } from 'reactstrap';
import { H5, Btn } from '../../../AbstractElements';
import { BTC, BuyCoins, DailyDropdown, EnterCryptoCoins, EnterMoneyConvertedTo, ETH, LTC, SellCoins, USD } from '../../../Constant';
import DropdownCommon from '../../Common/Dropdown';

const SellCard = () => {
  const handleSubmit = (e) => {
    e.preventDefault(0);
  };
  return (
    <Card>
      <CardHeader className='card-no-border'>
        <div className='header-top gap-1'>
          <H5>{SellCoins}</H5>
          <DropdownCommon dropdownMain={{ className: 'icon-dropdown', direction: 'start' }} options={DailyDropdown} iconName='icon-more-alt' btn={{ tag: 'span' }} />
        </div>
      </CardHeader>
      <CardBody className='pt-0'>
        <Form onSubmit={handleSubmit} className='theme-form crypto-form'>
          <div className='mb-3'>
            <Label className='form-label f-light' for='cryptoMony'>
              {EnterCryptoCoins}
            </Label>
            <div className='position-relative'>
              <Input className='form-control' id='cryptoMony' type='number' placeholder={100} />
              <select className='form-select crypto-select warning'>
                <option>{USD}</option>
                <option>{BTC}</option>
                <option>{LTC}</option>
                <option>{ETH}</option>
              </select>
            </div>
          </div>
          <div className='mb-3'>
            <Label className='form-label f-light' for='sellMony'>
              {EnterMoneyConvertedTo}
            </Label>
            <div className='position-relative'>
              <Input className='form-control' id='sellMony' type='number' placeholder='0.0043' />
              <select className='form-select crypto-select primary'>
                <option>{LTC}</option>
                <option>{BTC}</option>
                <option>{USD}</option>
                <option>{ETH}</option>
              </select>
            </div>
          </div>
          <Btn attrBtn={{ type: 'submit', color: 'primary', className: 'btn-hover-effect w-100' }}>{BuyCoins}</Btn>
        </Form>
      </CardBody>
    </Card>
  );
};

export default SellCard;
