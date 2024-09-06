import React, { Fragment, useContext, useState } from 'react';
import { Check } from 'react-feather';
import { toast } from 'react-toastify';
import TodoContext from '../../../_helper/Todo';

const TodoCheckbox = () => {
  const [markAll, setMarkAll] = useState(true);
  const { markAllItems } = useContext(TodoContext);
  const markAllStatus = () => {
    setMarkAll(!markAll);
    if (markAll === true) {
      toast.error('All Task In-Completed !');
    } else {
      toast.success('All Task Completed !');
    }
    markAllItems(markAll);
  };
  return (
    <Fragment>
      <div className='mark-all-tasks'>
        <div className='mark-all-tasks-container'>
          <span className='mark-all-btn d-flex align-items-center gap-1' id='mark-all-finished' role='button'>
            <span className='btn-label'>{'Mark all as finished'}</span>
            <span className='action-box completed' onClick={markAllStatus}>
              {markAll && <Check className='icon icon-check' />}
            </span>
          </span>
          <span className='mark-all-btn  d-flex align-items-center gap-1 move-down' id='mark-all-incomplete' role='button'>
            <span className='btn-label'>{'Mark all as Incomplete'}</span>
            <span className='action-box'>
              <Check className='icon icon-check' />
            </span>
          </span>
        </div>
      </div>
    </Fragment>
  );
};
export default TodoCheckbox;
