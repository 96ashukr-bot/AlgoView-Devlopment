import React from 'react';
import { TrendingDown, TrendingUp } from 'react-feather';
import { Table } from 'reactstrap';
import { H6 } from '../../../AbstractElements';

const TransactionTable = ({ tableData, filterCoins }) => {
  const updatedCoins = filterCoins === 'All' ? tableData : tableData.filter((item) => item.title.includes(filterCoins));
  return (
    <Table>
      <tbody>
        {updatedCoins?.map((item, i) => (
          <tr key={i}>
            <td>
              <div className='d-flex'>
                {item.trend === 'up' ? <TrendingUp className='font-success me-2' /> : <TrendingDown className='font-danger me-2' />}
                <div>
                  <H6 attrH6={{ className: 'f-14 mb-0' }}>{item.title}</H6>
                  <span className='f-light'>{item.subTitle}</span>
                </div>
              </div>
            </td>
            <td>
              <span className='f-light f-w-500'>
                {item.price} {item.coins}
              </span>
            </td>
            <td>
              <span className='f-light f-w-500'>${item.totalPrice}</span>
            </td>
          </tr>
        ))}
      </tbody>
    </Table>
  );
};

export default TransactionTable;
