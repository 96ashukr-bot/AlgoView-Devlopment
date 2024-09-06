import React from 'react';
import { TrendingDown, TrendingUp } from 'react-feather';
import { Card, CardBody, CardHeader, Table } from 'reactstrap';
import { H5, H6 } from '../../../AbstractElements';
import { MyCurrenciesTitle, Trade } from '../../../Constant';
import { MyCurrenciesTableData } from '../../../Data/Crypto';
import SvgIcon from '../../Common/Component/SvgIcon';

const MyCurrencies = () => {
  const tableHeader = ['Coin Name', 'Price', '24h Change', 'Total Balance', 'Total Coin', 'Action'];
  return (
    <Card>
      <CardHeader className='card-no-border'>
        <div className='header-top'>
          <H5>{MyCurrenciesTitle}</H5>
        </div>
      </CardHeader>
      <CardBody className='pt-0'>
        <div className='recent-table table-responsive currency-table'>
          <Table>
            <thead>
              <tr>
                {tableHeader.map((item, i) => (
                  <th key={i} className='f-light'>
                    {item}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {MyCurrenciesTableData.map((item, i) => (
                <tr key={i}>
                  <td>
                    <div className='d-flex align-items-center gap-2'>
                      <div className={`currency-icon ${item.color}`}>
                        <SvgIcon iconId={item.icon} />
                      </div>
                      <div>
                        <H6 attrH6={{ className: 'f-14 mb-0 f-w-400' }}>{item.title}</H6>
                      </div>
                    </div>
                  </td>
                  <td>${item.price}</td>
                  <td>
                    <div className={`change-currency font-${item.status}`}>
                      {item.status === 'success' ? <TrendingUp className='me-1' /> : <TrendingDown className='me-1' />}
                      {item.gros}
                    </div>
                  </td>
                  <td>${item.totalBalance}</td>
                  <td>{item.totalCoin}</td>
                  <td>
                    <button className='btn badge-light-primary'>{Trade}</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </div>
      </CardBody>
    </Card>
  );
};

export default MyCurrencies;
