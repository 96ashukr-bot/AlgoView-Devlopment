import React from 'react';
import { TrendingDown, TrendingUp } from 'react-feather';
import { Card, CardBody, CardHeader, Table } from 'reactstrap';
import { H5 } from '../../../AbstractElements';
import { AllCampaignsTitle, DailyDropdown } from '../../../Constant';
import { AllCampaignsTable } from '../../../Data/Social';
import DropdownCommon from '../../Common/Dropdown';

const AllCampaigns = () => {
  return (
    <Card>
      <CardHeader className='card-no-border'>
        <div className='header-top'>
          <H5 className='m-0'>{AllCampaignsTitle}</H5>
          <div className='card-header-right-icon'>
            <DropdownCommon dropdownMain={{ className: 'icon-dropdown', direction: 'start' }} options={DailyDropdown} iconName='icon-more-alt' btn={{ tag: 'span' }} />
          </div>
        </div>
      </CardHeader>
      <CardBody className='pt-0 campaign-table'>
        <div className='recent-table table-responsive currency-table'>
          <Table>
            <thead>
              <tr>
                {AllCampaignsTable.header.map((item, i) => (
                  <th key={i} className='f-light'>
                    {item}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {AllCampaignsTable.body.map((item, i) => (
                <tr key={i}>
                  <td className={`border-icon ${item.ADPlatform}`}>
                    <div>
                      <div className='social-circle'>
                        <i className={`fa fa-${item.icon}`} />
                      </div>
                    </div>
                  </td>
                  <td>{item.campaign}</td>
                  <td>{item.GEO}</td>
                  <td>
                    <div className='change-currency'>
                      {item.profitability > 40 ? <TrendingUp className='font-success me-1' /> : <TrendingDown className='font-danger me-1' />}
                      {item.profitability}%
                    </div>
                  </td>
                  <td>${item.maxParticipation}</td>
                  <td>
                    <button className={`btn badge-light-${item.status === 'Inactive' ? 'light' : 'primary'} ${item.status === 'Inactive' && 'disabled'}`}>{item.status}</button>
                  </td>
                  <td>
                    <button className='plus-btn'>+ </button>
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

export default AllCampaigns;
