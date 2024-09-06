import React from 'react';
import DataTable from 'react-data-table-component';
import { MoreVertical } from 'react-feather';
import { Link } from 'react-router-dom';
import { Image } from '../../../../AbstractElements';
import { OrderHistoryDataTable } from '../../../../Data/Ecommerce/Orderhistory';

const OrderHistoryTable = () => {
  const updatedData = {
    ...OrderHistoryDataTable,
    productRow: OrderHistoryDataTable.productRow.map((item) => {
      return {
        product: <Image attrImage={{ className: 'img-fluid img-30 border-0', src: require(`../../../../assets/images/product/${item.product}`), alt: '' }} />,
        productName: (
          <div className='product-name'>
            <Link to='#javascript'> {item.productName}</Link>
            <div className='order-process'>
              <span className={`order-process-circle ${item.statusCode ? item.statusCode : ''}`}></span>
              {item.status}
            </div>
          </div>
        ),
        size: item.size,
        color: item.color,
        articleNumber: item.articleNumber,
        units: item.units,
        price: item.price,
        action: <MoreVertical />,
      };
    }),
    productColumns: [
      ...OrderHistoryDataTable.productColumns,
      {
        name: <i className='fa fa-angle-down' />,
        selector: (row) => row.action,
        sortable: false,
        center: true,
        minWidth: '50px',
        maxWidth: '60px',
      },
    ],
  };
  return (
    <div className='table-responsive table-bordernone orderHistoryTable product-table'>
      <DataTable pagination paginationServer columns={updatedData.productColumns} data={updatedData.productRow} highlightOnHover={true} striped={true} responsive={true} />
    </div>
  );
};

export default OrderHistoryTable;
