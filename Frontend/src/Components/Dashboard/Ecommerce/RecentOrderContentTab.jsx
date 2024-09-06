import React from 'react';
import { RecentOrderTable } from '../../../Data/Ecommerce';
import { Link } from 'react-router-dom';
import { TabContent, Table, TabPane } from 'reactstrap';
import { Image, H6 } from '../../../AbstractElements';
import SvgIcon from '../../Common/Component/SvgIcon';
const RecentOrderContentTab = ({ RecentOrdersNav, isActive, show }) => {
  return (
    <TabContent activeTab={isActive}>
      {RecentOrdersNav.map((_, i) => {
        return (
          <TabPane key={i} className={`fade ${isActive === `${i}` ? show : ''}`} tabId={`${i}`}>
            <div className='recent-table table-responsive'>
              <Table>
                <thead>
                  <tr>
                    <th className='f-light'>Item</th>
                    <th className='f-light'>Qty</th>
                    <th className='f-light'>Price</th>
                    <th className='f-light'>Status</th>
                    <th className='f-light'>Total Price</th>
                  </tr>
                </thead>
                <tbody>
                  {RecentOrderTable[i].map((item, j) => (
                    <tr key={j}>
                      <td>
                        <div className='product-content'>
                          <div className='order-image'>
                            <Image attrImage={{ src: require(`../../../assets/images/dashboard-2/order/sub-product/${item.image}`), alt: 't-shirt' }} />
                          </div>
                          <div>
                            <H6 attrH6={{ className: 'f-14 mb-0' }}>
                              <Link to={`/app/ecommerce/orderhistory`}>{item.title}</Link>
                            </H6>
                            <span className='f-light f-12'>Id : {item.id}</span>
                          </div>
                        </div>
                      </td>
                      <td className='f-w-500'>{item.qty}</td>
                      <td className='f-w-500'>${item.price}</td>
                      <td className='f-w-500'>
                        <div className={`recent-status font-${item.statusCode}`}>
                          <SvgIcon iconId={item.iconName} className='me-1' />
                          {item.status}
                        </div>
                      </td>
                      <td className='f-w-500'>${item.total}</td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </div>
          </TabPane>
        );
      })}
    </TabContent>
  );
};

export default RecentOrderContentTab;
