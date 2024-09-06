import React from 'react';
import ReactApexChart from 'react-apexcharts';
import { Card, CardBody, CardHeader, Col, Row, Table } from 'reactstrap';
import { H5, H6 } from '../../../AbstractElements';
import { CryptoDropdown, MyPortfolioTitle } from '../../../Constant';
import { portfolioLegend } from '../../../Data/Crypto';
import { myPortfolioChartOption } from '../../../Data/Crypto/Chart';
import SvgIcon from '../../Common/Component/SvgIcon';
import DropdownCommon from '../../Common/Dropdown';

const MyPortfolio = () => {
  return (
    <Card className='portfolio-card'>
      <CardHeader className='card-no-border'>
        <div className='header-top'>
          <H5 className='m-0'>{MyPortfolioTitle}</H5>
          <div className='card-header-right-icon'>
            <DropdownCommon icon={false} options={CryptoDropdown} btn={{ caret: true, direction: 'end' }} />
          </div>
        </div>
      </CardHeader>
      <CardBody>
        <Row>
          <Col xxl='12' xl='7' sm='6' className='box-col-6'>
            <div className='portfolio-chart-container'>
              <ReactApexChart type='radialBar' height={280} options={myPortfolioChartOption.options} series={myPortfolioChartOption.series} />
            </div>
          </Col>
          <Col xxl='12' xl='5' sm='6' className='box-col-6'>
            <div className='portfolio-table recent-table table-responsive'>
              <Table>
                <tbody>
                  {portfolioLegend.map((item, i) => (
                    <tr key={i}>
                      <td>
                        <div className='d-flex align-items-center gap-2'>
                          <div className={`currency-icon ${item.color}`}>
                            <SvgIcon iconId={item.icon} />
                          </div>
                          <div>
                            <H6 attrH6={{ className: 'f-14 mb-1' }}>{item.title}</H6>
                            <div className='d-flex align-items-center gap-1'>
                              <span className={`status bg-${item.status}`} />
                              <span className='f-light'>{item.subTitle}</span>
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className='text-end'>
                        <H6 attrH6={{ className: 'f-14 f-w-400 mb-1' }}>
                          {item.subTitle} {item.price}
                        </H6>
                        <span className={`font-${item.status}`}>${item.totalPrice}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </div>
          </Col>
        </Row>
      </CardBody>
    </Card>
  );
};

export default MyPortfolio;
