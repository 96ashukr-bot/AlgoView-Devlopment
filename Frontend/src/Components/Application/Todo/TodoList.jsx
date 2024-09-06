import React, { useState, Fragment, useContext } from 'react';
import { toast } from 'react-toastify';

import TodoContext from '../../../_helper/Todo';
import { H4, H5, LI, UL } from '../../../AbstractElements';

const TodoList = () => {
  const { allTodos, removeItems, selectedItem } = useContext(TodoContext);

  const [status, setStatus] = useState('pending');

  const handleRemoveTodo = (todoId) => {
    removeItems(todoId);
    toast.success('Deleted Task !');
  };
  const handleMarkedTodo = (itemId, itemStatus) => {
    if (itemStatus === 'completed') {
      setStatus('pending');
      selectedItem(itemId, status);
      toast.success('Task Completed !');
    } else if (itemStatus === 'pending') {
      setStatus('completed');
      selectedItem(itemId, status);
      toast.error(' Task In-completed !');
    }
  };

  return (
    <Fragment>
      <div className='todo-list-body'>
        <UL attrUL={{ className: 'simple-list', id: 'todo-list' }}>
          {allTodos.length > 0
            ? allTodos.map((todo, index) => (
                <LI attrLI={{ className: 'task border-0 ' + todo.status }} key={index}>
                  <div className='task-container'>
                    <H4 attrH4={{ className: 'task-label' }}>{todo.title}</H4>
                    <div className='d-flex align-items-center gap-4'>
                      <span className={`badge badge-light-${todo.statusCode}`}>{todo.status}</span>
                      <H5 attrH5={{ className: 'assign-name m-0' }}>{todo.date}</H5>
                      <span className='task-action-btn'>
                        <span className='action-box large delete-btn' title='Delete Task' onClick={() => handleRemoveTodo(todo.id)}>
                          <i className='icon'>
                            <i className='icon-trash'></i>
                          </i>
                        </span>
                        <span className='action-box large complete-btn' title='Mark Complete' onClick={() => handleMarkedTodo(todo.id, status)}>
                          <i className='icon'>
                            <i className='icon-check'></i>
                          </i>
                        </span>
                      </span>
                    </div>
                  </div>
                </LI>
              ))
            : ''}
        </UL>
      </div>
    </Fragment>
  );
};
export default TodoList;
