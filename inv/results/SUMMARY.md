# scipy.linalg inv/solve across versions

| scipy | case | cond | inv residual | solve residual |
|---|---|---|---|---|
| 1.16.3 | real_symmetric | 1.939 | 1.144e-16 | 2.289e-16 |
| 1.16.3 | complex_symmetric | 2.915 | 3.405e-16 | 7.850e-17 |
| 1.16.3 | hermitian | 4.000 | 0.000e+00 | 1.923e-16 |
| 1.16.3 | general_complex | 4.729 | 2.776e-16 | 2.220e-16 |
| 1.16.3 | ybus_3node | 12.689 | 1.702e-15 | 2.150e-16 |
| 1.16.3 | net_A_resistive | 2.312 | 3.409e-16 | 1.129e-16 |
| 1.16.3 | net_B_reactive | 16.178 | 1.261e-15 | 2.677e-16 |
| 1.17.0 | real_symmetric | 1.939 | 1.144e-16 | 1.110e-16 |
| 1.17.0 | complex_symmetric | 2.915 | 1.601e+00 | 1.479e+00 |
| 1.17.0 | hermitian | 4.000 | 3.608e-16 | 4.710e-16 |
| 1.17.0 | general_complex | 4.729 | 1.110e-16 | 2.220e-16 |
| 1.17.0 | ybus_3node | 12.689 | 8.354e-16 | 2.355e-16 |
| 1.17.0 | net_A_resistive | 2.312 | 4.921e-01 | 1.777e-01 |
| 1.17.0 | net_B_reactive | 16.178 | 8.408e-16 | 2.604e-16 |
| 1.17.1 | real_symmetric | 1.939 | 1.144e-16 | 1.110e-16 |
| 1.17.1 | complex_symmetric | 2.915 | 1.576e-16 | 1.360e-16 |
| 1.17.1 | hermitian | 4.000 | 3.608e-16 | 4.710e-16 |
| 1.17.1 | general_complex | 4.729 | 1.110e-16 | 2.220e-16 |
| 1.17.1 | ybus_3node | 12.689 | 8.354e-16 | 2.355e-16 |
| 1.17.1 | net_A_resistive | 2.312 | 1.461e-16 | 6.435e-17 |
| 1.17.1 | net_B_reactive | 16.178 | 8.408e-16 | 2.604e-16 |
| 1.18.1 | real_symmetric | 1.939 | 1.144e-16 | 1.110e-16 |
| 1.18.1 | complex_symmetric | 2.915 | 1.057e-16 | 7.850e-17 |
| 1.18.1 | hermitian | 4.000 | 4.098e-16 | 4.711e-16 |
| 1.18.1 | general_complex | 4.729 | 2.776e-16 | 2.220e-16 |
| 1.18.1 | ybus_3node | 12.689 | 7.555e-16 | 2.355e-16 |
| 1.18.1 | net_A_resistive | 2.312 | 2.461e-16 | 1.129e-16 |
| 1.18.1 | net_B_reactive | 16.178 | 1.248e-15 | 2.677e-16 |

## scipy 1.16.3 (numpy 2.3.5)
- real_symmetric: solve = ['0.272727+0.000000j', '-0.090909+0.000000j'] ; true_solve = ['0.272727+0.000000j', '-0.090909+0.000000j'] ; hermitian-reading min eig = 2.381966011250105 ; predicted if Cholesky path = ['0.272727+0.000000j', '-0.090909+0.000000j']
- complex_symmetric: solve = ['0.529412-0.117647j', '-0.235294-0.058824j'] ; true_solve = ['0.529412-0.117647j', '-0.235294-0.058824j'] ; hermitian-reading min eig = 0.9999999999999993 ; predicted if Cholesky path = ['0.750000+0.000000j', '-0.250000+0.250000j']
- hermitian: solve = ['0.750000+0.000000j', '-0.250000+0.250000j'] ; true_solve = ['0.750000+0.000000j', '-0.250000+0.250000j'] ; hermitian-reading min eig = 0.9999999999999993 ; predicted if Cholesky path = ['0.750000+0.000000j', '-0.250000+0.250000j']
- general_complex: solve = ['0.594595-0.432432j', '-0.445946-0.175676j'] ; true_solve = ['0.594595-0.432432j', '-0.445946-0.175676j'] ; hermitian-reading min eig = 0.9999999999999993 ; predicted if Cholesky path = ['0.750000+0.000000j', '-0.250000-0.250000j']
- ybus_3node: solve = ['1.000183-1.025328j', '0.815238-1.377416j', '0.853228-1.342802j'] ; true_solve = ['1.000183-1.025328j', '0.815238-1.377416j', '0.853228-1.342802j'] ; hermitian-reading min eig = -0.4307585281945485 ; predicted if Cholesky path = None
- net_A_resistive: solve = ['0.167357+0.011977j', '0.058355-0.014105j', '0.042831-0.014376j'] ; true_solve = ['0.167357+0.011977j', '0.058355-0.014105j', '0.042831-0.014376j'] ; hermitian-reading min eig = 1.6137572789383618 ; predicted if Cholesky path = ['0.177348+0.000000j', '0.060044+0.025845j', '0.040327+0.026847j']
- net_B_reactive: solve = ['0.142473-0.564338j', '0.125546-0.674272j', '0.118851-0.706271j'] ; true_solve = ['0.142473-0.564338j', '0.125546-0.674272j', '0.118851-0.706271j'] ; hermitian-reading min eig = -1.952019456659321 ; predicted if Cholesky path = None
## scipy 1.17.0 (numpy 2.3.5)
- real_symmetric: solve = ['0.272727+0.000000j', '-0.090909+0.000000j'] ; true_solve = ['0.272727+0.000000j', '-0.090909+0.000000j'] ; hermitian-reading min eig = 2.381966011250105 ; predicted if Cholesky path = ['0.272727+0.000000j', '-0.090909+0.000000j']
- complex_symmetric: solve = ['0.750000+0.000000j', '-0.250000+0.250000j'] ; true_solve = ['0.529412-0.117647j', '-0.235294-0.058824j'] ; hermitian-reading min eig = 0.9999999999999993 ; predicted if Cholesky path = ['0.750000+0.000000j', '-0.250000+0.250000j']
- hermitian: solve = ['0.750000+0.000000j', '-0.250000+0.250000j'] ; true_solve = ['0.750000+0.000000j', '-0.250000+0.250000j'] ; hermitian-reading min eig = 0.9999999999999993 ; predicted if Cholesky path = ['0.750000+0.000000j', '-0.250000+0.250000j']
- general_complex: solve = ['0.594595-0.432432j', '-0.445946-0.175676j'] ; true_solve = ['0.594595-0.432432j', '-0.445946-0.175676j'] ; hermitian-reading min eig = 0.9999999999999993 ; predicted if Cholesky path = ['0.750000+0.000000j', '-0.250000-0.250000j']
- ybus_3node: solve = ['1.000183-1.025328j', '0.815238-1.377416j', '0.853228-1.342802j'] ; true_solve = ['1.000183-1.025328j', '0.815238-1.377416j', '0.853228-1.342802j'] ; hermitian-reading min eig = -0.4307585281945485 ; predicted if Cholesky path = None
- net_A_resistive: solve = ['0.177348-0.000000j', '0.060044+0.025845j', '0.040327+0.026847j'] ; true_solve = ['0.167357+0.011977j', '0.058355-0.014105j', '0.042831-0.014376j'] ; hermitian-reading min eig = 1.6137572789383623 ; predicted if Cholesky path = ['0.177348+0.000000j', '0.060044+0.025845j', '0.040327+0.026847j']
- net_B_reactive: solve = ['0.142473-0.564338j', '0.125546-0.674272j', '0.118851-0.706271j'] ; true_solve = ['0.142473-0.564338j', '0.125546-0.674272j', '0.118851-0.706271j'] ; hermitian-reading min eig = -1.9520194566593223 ; predicted if Cholesky path = None
## scipy 1.17.1 (numpy 2.3.5)
- real_symmetric: solve = ['0.272727+0.000000j', '-0.090909+0.000000j'] ; true_solve = ['0.272727+0.000000j', '-0.090909+0.000000j'] ; hermitian-reading min eig = 2.381966011250105 ; predicted if Cholesky path = ['0.272727+0.000000j', '-0.090909+0.000000j']
- complex_symmetric: solve = ['0.529412-0.117647j', '-0.235294-0.058824j'] ; true_solve = ['0.529412-0.117647j', '-0.235294-0.058824j'] ; hermitian-reading min eig = 0.9999999999999993 ; predicted if Cholesky path = ['0.750000+0.000000j', '-0.250000+0.250000j']
- hermitian: solve = ['0.750000+0.000000j', '-0.250000+0.250000j'] ; true_solve = ['0.750000+0.000000j', '-0.250000+0.250000j'] ; hermitian-reading min eig = 0.9999999999999993 ; predicted if Cholesky path = ['0.750000+0.000000j', '-0.250000+0.250000j']
- general_complex: solve = ['0.594595-0.432432j', '-0.445946-0.175676j'] ; true_solve = ['0.594595-0.432432j', '-0.445946-0.175676j'] ; hermitian-reading min eig = 0.9999999999999993 ; predicted if Cholesky path = ['0.750000+0.000000j', '-0.250000-0.250000j']
- ybus_3node: solve = ['1.000183-1.025328j', '0.815238-1.377416j', '0.853228-1.342802j'] ; true_solve = ['1.000183-1.025328j', '0.815238-1.377416j', '0.853228-1.342802j'] ; hermitian-reading min eig = -0.4307585281945485 ; predicted if Cholesky path = None
- net_A_resistive: solve = ['0.167357+0.011977j', '0.058355-0.014105j', '0.042831-0.014376j'] ; true_solve = ['0.167357+0.011977j', '0.058355-0.014105j', '0.042831-0.014376j'] ; hermitian-reading min eig = 1.6137572789383623 ; predicted if Cholesky path = ['0.177348+0.000000j', '0.060044+0.025845j', '0.040327+0.026847j']
- net_B_reactive: solve = ['0.142473-0.564338j', '0.125546-0.674272j', '0.118851-0.706271j'] ; true_solve = ['0.142473-0.564338j', '0.125546-0.674272j', '0.118851-0.706271j'] ; hermitian-reading min eig = -1.9520194566593223 ; predicted if Cholesky path = None
## scipy 1.18.1 (numpy 2.3.5)
- real_symmetric: solve = ['0.272727+0.000000j', '-0.090909+0.000000j'] ; true_solve = ['0.272727+0.000000j', '-0.090909+0.000000j'] ; hermitian-reading min eig = 2.381966011250105 ; predicted if Cholesky path = ['0.272727+0.000000j', '-0.090909+0.000000j']
- complex_symmetric: solve = ['0.529412-0.117647j', '-0.235294-0.058824j'] ; true_solve = ['0.529412-0.117647j', '-0.235294-0.058824j'] ; hermitian-reading min eig = 0.9999999999999993 ; predicted if Cholesky path = ['0.750000+0.000000j', '-0.250000+0.250000j']
- hermitian: solve = ['0.750000-0.000000j', '-0.250000+0.250000j'] ; true_solve = ['0.750000+0.000000j', '-0.250000+0.250000j'] ; hermitian-reading min eig = 0.9999999999999993 ; predicted if Cholesky path = ['0.750000+0.000000j', '-0.250000+0.250000j']
- general_complex: solve = ['0.594595-0.432432j', '-0.445946-0.175676j'] ; true_solve = ['0.594595-0.432432j', '-0.445946-0.175676j'] ; hermitian-reading min eig = 0.9999999999999993 ; predicted if Cholesky path = ['0.750000+0.000000j', '-0.250000-0.250000j']
- ybus_3node: solve = ['1.000183-1.025328j', '0.815238-1.377416j', '0.853228-1.342802j'] ; true_solve = ['1.000183-1.025328j', '0.815238-1.377416j', '0.853228-1.342802j'] ; hermitian-reading min eig = -0.4307585281945485 ; predicted if Cholesky path = None
- net_A_resistive: solve = ['0.167357+0.011977j', '0.058355-0.014105j', '0.042831-0.014376j'] ; true_solve = ['0.167357+0.011977j', '0.058355-0.014105j', '0.042831-0.014376j'] ; hermitian-reading min eig = 1.6137572789383618 ; predicted if Cholesky path = ['0.177348+0.000000j', '0.060044+0.025845j', '0.040327+0.026847j']
- net_B_reactive: solve = ['0.142473-0.564338j', '0.125546-0.674272j', '0.118851-0.706271j'] ; true_solve = ['0.142473-0.564338j', '0.125546-0.674272j', '0.118851-0.706271j'] ; hermitian-reading min eig = -1.952019456659321 ; predicted if Cholesky path = None
