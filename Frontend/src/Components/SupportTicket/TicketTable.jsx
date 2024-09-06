import { supportColumns, supportData } from '../../Data/SupportTicket';
import React, { Fragment } from 'react';
import DataTable from 'react-data-table-component';

const TicketTable = () => {
    return (
        <Fragment>
            <div className="table-responsive support-table">
                <DataTable
                    columns={supportColumns}
                    data={supportData}
                    striped={true}
                    center={true}
                    pagination
                />
            </div>
        </Fragment>
    );
};
export default TicketTable;