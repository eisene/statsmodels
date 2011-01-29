from cStringIO import StringIO
import numpy as np

_default_table_fmt = dict(
    empty_cell = '',
    colsep='  ',
    row_pre = '',
    row_post = '',
    table_dec_above='=',
    table_dec_below='=',
    header_dec_below='-',
    header_fmt = '%s',
    stub_fmt = '%s',
    title_align='c',
    header_align = 'r',
    data_aligns = 'r',
    stubs_align = 'l',
    fmt = 'txt'
)

class VARSummary(object):
    default_fmt = dict(
        #data_fmts = ["%#12.6g","%#12.6g","%#10.4g","%#5.4g"],
        #data_fmts = ["%#10.4g","%#10.4g","%#10.4g","%#6.4g"],
        data_fmts = ["%#15.6F","%#15.6F","%#15.3F","%#14.3F"],
        empty_cell = '',
        #colwidths = 10,
        colsep='  ',
        row_pre = '',
        row_post = '',
        table_dec_above='=',
        table_dec_below='=',
        header_dec_below='-',
        header_fmt = '%s',
        stub_fmt = '%s',
        title_align='c',
        header_align = 'r',
        data_aligns = 'r',
        stubs_align = 'l',
        fmt = 'txt'
    )

    part1_fmt = dict(default_fmt,
        data_fmts = ["%s"],
        colwidths = 15,
        colsep=' ',
        table_dec_below='',
        header_dec_below=None,
    )
    part2_fmt = dict(default_fmt,
        data_fmts = ["%#12.6g","%#12.6g","%#10.4g","%#5.4g"],
        colwidths = None,
        colsep='    ',
        table_dec_above='-',
        table_dec_below='-',
        header_dec_below=None,
    )

    def __init__(self, estimator):
        self.model = estimator
        self.summary = self.make()

    def __repr__(self):
        return self.summary

    def _lag_names(self):
        lag_names = []

        # take care of lagged endogenous names
        for i in range(1, self.model.p+1):
            for name in self.model.names:
                lag_names.append('L'+str(i)+'.'+name)

        # put them together
        Xnames = lag_names

        # handle the constant name
        trendorder = 1 # self.trendorder
        if trendorder != 0:
            Xnames.insert(0, 'const')
        if trendorder > 1:
            Xnames.insert(0, 'trend')
        if trendorder > 2:
            Xnames.insert(0, 'trend**2')

        return Xnames

    def make(self, endog_names=None, exog_names=None):
        """
        Summary of VAR model
        """
        buf = StringIO()

        print >> buf, self._header_table()
        # print >> buf, self._stats_table()

        print >> buf, self._coef_table()
        print >> buf, self._resid_info()

        return buf.getvalue()

    def _header_table(self):
        import time

        model = self.model

        t = time.localtime()
        # ncoefs = len(model.beta) #TODO: change when we allow coef restrictions

        # Header information
        part1title = "Summary of Regression Results"
        part1data = [[model._model_type],
                     ["OLS"], #TODO: change when fit methods change
                     [time.strftime("%a, %d, %b, %Y", t)],
                     [time.strftime("%H:%M:%S", t)]]
        part1header = None
        part1stubs = ('Model:',
                     'Method:',
                     'Date:',
                     'Time:')
        part1 = SimpleTable(part1data, part1header, part1stubs,
                            title=part1title, txt_fmt=self.part1_fmt)

        return str(part1)

    def _stats_table(self):
        # TODO: do we want individual statistics or should users just
        # use results if wanted?
        # Handle overall fit statistics
        part2Lstubs = ('No. of Equations:',
                       'Nobs:',
                       'Log likelihood:',
                       'AIC:')
        part2Rstubs = ('BIC:',
                       'HQIC:',
                       'FPE:',
                       'Det(Omega_mle):')
        part2Ldata = [[self.neqs],[self.nobs],[self.llf],[self.aic]]
        part2Rdata = [[self.bic],[self.hqic],[self.fpe],[self.detomega]]
        part2Lheader = None
        part2L = SimpleTable(part2Ldata, part2Lheader, part2Lstubs,
                             txt_fmt = self.part2_fmt)
        part2R = SimpleTable(part2Rdata, part2Lheader, part2Rstubs,
                             txt_fmt = self.part2_fmt)
        part2L.extend_right(part2R)

        return str(part2L)

    def _coef_table(self):
        model = self.model
        k = model.k

        Xnames = self._lag_names()

        data = zip(model.beta.ravel(),
                   model.stderr.ravel(),
                   model.t().ravel(),
                   model.pvalues.ravel())

        header = ('coefficient','std. error','t-stat','prob')

        buf = StringIO()
        dim = k * model.p + 1
        for i in range(k):
            section = "Results for equation %s" % model.names[i]
            print >> buf, section

            table = SimpleTable(data[dim * i : dim * (i + 1)], header,
                                Xnames, title=None, txt_fmt = self.default_fmt)

            print >> buf, str(table)

            if i < k - 1: buf.write('\n')

        return buf.getvalue()

    def _resid_info(self):
        buf = StringIO()
        names = self.model.names

        resid_cov = np.cov(self.model.resid, rowvar=0)
        rdiag = np.sqrt(np.diag(resid_cov))
        resid_corr = resid_cov / np.outer(rdiag, rdiag)

        print >> buf, "Correlation matrix of residuals"
        print >> buf, pprint_matrix(resid_corr, names, names)

        return buf.getvalue()
